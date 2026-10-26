package com.example.wrongbook.service.impl;

import com.example.wrongbook.service.LlmClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Mock 大模型网关：不调用真实 API，按提示词中的任务标记返回固定结构的 JSON，
 * 供无 API Key 环境下开发与演示。知识点归类采用"题干关键词命中候选知识点"模拟。
 * 接入真实大模型时新增 OpenAiLlmClient / DashScopeClient 并修改 app.llm.provider。
 */
@Component
@ConditionalOnProperty(name = "app.llm.provider", havingValue = "mock")
public class MockLlmClient implements LlmClient {

    /** 解析任务与变式任务的提示词标记（由调用方组装提示词时写入） */
    public static final String TASK_ANALYZE = "任务：错题解析";
    public static final String TASK_VARIANT = "任务：变式题生成";

    private static final int EMBED_DIM = 8;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public String chat(String prompt) {
        if (prompt.contains(TASK_ANALYZE)) {
            return mockAnalyze(prompt);
        }
        if (prompt.contains(TASK_VARIANT)) {
            return mockVariant(prompt);
        }
        return "{\"text\":\"Mock 响应：未识别的任务类型\"}";
    }

    @Override
    public List<Double> embed(String text) {
        // 确定性伪向量：按字符落入 8 个桶的分布生成，语义相近的文本向量相近
        double[] buckets = new double[EMBED_DIM];
        for (char c : text.toCharArray()) {
            buckets[Math.floorMod(c, EMBED_DIM)] += 1.0;
        }
        double norm = 0;
        for (double v : buckets) {
            norm += v * v;
        }
        norm = Math.sqrt(norm);
        List<Double> vector = new ArrayList<>(EMBED_DIM);
        for (double v : buckets) {
            vector.add(norm == 0 ? 0 : Math.round(v / norm * 10000.0) / 10000.0);
        }
        return vector;
    }

    @Override
    public String model() {
        return "mock-llm";
    }

    /** 解析任务 Mock：从提示词的候选知识点段中选择题干命中的知识点，输出结构化 JSON */
    private String mockAnalyze(String prompt) {
        String stem = section(prompt, "题干：", "\n");
        Map<Long, String> candidates = parseCandidates(prompt);
        Long kpId = null;
        String kpName = "未归类";
        for (Map.Entry<Long, String> e : candidates.entrySet()) {
            if (!stem.isEmpty() && stem.contains(e.getValue())) {
                kpId = e.getKey();
                kpName = e.getValue();
                break;
            }
        }
        if (kpId == null && !candidates.isEmpty()) {
            Map.Entry<Long, String> first = candidates.entrySet().iterator().next();
            kpId = first.getKey();
            kpName = first.getKey() == 0 ? "未归类" : first.getValue();
        }
        int difficulty = stem.length() > 80 ? 4 : stem.length() > 30 ? 3 : 2;
        ObjectNode json = objectMapper.createObjectNode();
        if (kpId != null && kpId != 0) {
            json.put("knowledgePointId", kpId);
        } else {
            json.putNull("knowledgePointId");
        }
        json.put("errorCause", "（Mock 生成）本题考查「" + kpName + "」。常见错因：对"
                + kpName + "的基本概念理解不牢，已知条件与所求目标之间的转化思路不清晰，"
                + "或计算过程中出现符号、代入错误。");
        json.put("analysis", "（Mock 生成，接入真实大模型后此处为结合本地参考题的 RAG 解析）\n"
                + "1. 知识点定位：本题属于「" + kpName + "」。\n"
                + "2. 解题思路：先梳理题干已知条件，明确所求目标，再调用「" + kpName
                + "」的相关性质与公式逐步推导。\n"
                + "3. 易错提醒：注意条件适用范围与计算细节，完成后代回验证。");
        json.put("difficulty", difficulty);
        return json.toString();
    }

    /** 变式任务 Mock：输出 3 道模板化变式题 JSON */
    private String mockVariant(String prompt) {
        String stem = section(prompt, "原题题干：", "\n");
        String kpName = section(prompt, "知识点：", "\n");
        ObjectNode json = objectMapper.createObjectNode();
        ArrayNode variants = json.putArray("variants");
        String[] templates = {
                "（Mock 变式·基础）将原题中的数值条件调小后重新求解：" + abbreviate(stem),
                "（Mock 变式·巩固）交换原题的条件与所问，考查逆向运用：" + abbreviate(stem),
                "（Mock 变式·提升）在原题基础上增加一个限制条件，综合考查「" + kpName + "」：" + abbreviate(stem)
        };
        int[] difficulties = {2, 3, 4};
        for (int i = 0; i < templates.length; i++) {
            ObjectNode v = variants.addObject();
            v.put("stem", templates[i]);
            v.put("answer", "（Mock 生成）参考答案：依据「" + kpName + "」相关性质求解，步骤同原题。");
            v.put("difficulty", difficulties[i]);
        }
        return json.toString();
    }

    /** 解析提示词中"候选知识点："段（每行 "id:名称"） */
    private Map<Long, String> parseCandidates(String prompt) {
        Map<Long, String> candidates = new LinkedHashMap<>();
        String seg = section(prompt, "候选知识点：", "参考题目：");
        for (String line : seg.split("\n")) {
            line = line.trim();
            int idx = line.indexOf(':');
            if (idx > 0) {
                try {
                    candidates.put(Long.parseLong(line.substring(0, idx)), line.substring(idx + 1).trim());
                } catch (NumberFormatException ignored) {
                    // 非候选行跳过
                }
            }
        }
        return candidates;
    }

    /** 截取 prompt 中 start 与 end 之间的内容 */
    private String section(String prompt, String start, String end) {
        int i = prompt.indexOf(start);
        if (i < 0) {
            return "";
        }
        i += start.length();
        int j = prompt.indexOf(end, i);
        return (j < 0 ? prompt.substring(i) : prompt.substring(i, j)).trim();
    }

    private String abbreviate(String stem) {
        return stem.length() > 60 ? stem.substring(0, 60) + "…" : stem;
    }
}
