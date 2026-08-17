package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.ReviewPlan;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.PracticeRecordMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.ReviewPlanMapper;
import com.example.wrongbook.service.MessageService;
import com.example.wrongbook.service.ReportService;
import com.example.wrongbook.vo.WeeklyReportVO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ReportServiceImpl implements ReportService {

    private final QuestionMapper questionMapper;
    private final ReviewPlanMapper reviewPlanMapper;
    private final PracticeRecordMapper practiceRecordMapper;
    private final KnowledgePointMapper knowledgePointMapper;
    private final MessageService messageService;

    @Override
    public WeeklyReportVO weekly() {
        // 学生返回本人数据；教师不限制 userId，返回科目维度聚合（教师班级视角缺口占位）
        Long userId = "student".equals(UserContext.getRole()) ? UserContext.getUserId() : null;
        LocalDate weekStart = LocalDate.now().with(DayOfWeek.MONDAY);
        LocalDateTime weekStartTime = weekStart.atStartOfDay();

        WeeklyReportVO vo = new WeeklyReportVO();
        vo.setWeekStart(weekStart.format(DateTimeFormatter.ISO_LOCAL_DATE));

        // 错题总量与本周新增
        LambdaQueryWrapper<Question> baseWrapper = new LambdaQueryWrapper<>();
        baseWrapper.eq(userId != null, Question::getUserId, userId);
        vo.setTotalQuestionCount(questionMapper.selectCount(baseWrapper));
        LambdaQueryWrapper<Question> weekWrapper = new LambdaQueryWrapper<>();
        weekWrapper.eq(userId != null, Question::getUserId, userId)
                .ge(Question::getCreateTime, weekStartTime);
        vo.setNewQuestionCount(questionMapper.selectCount(weekWrapper));

        // 掌握度均值
        List<Question> all = questionMapper.selectList(baseWrapper.clone()
                .select(Question::getId, Question::getMastery));
        vo.setMasteryAvg(all.isEmpty() ? 0.0
                : Math.round(all.stream().mapToInt(Question::getMastery).average().orElse(0) * 10.0) / 10.0);

        // 复习完成率：本周应完成（plan_date 在本周）与已完成
        LambdaQueryWrapper<ReviewPlan> reviewWrapper = new LambdaQueryWrapper<>();
        reviewWrapper.eq(userId != null, ReviewPlan::getUserId, userId)
                .ge(ReviewPlan::getPlanDate, weekStart)
                .le(ReviewPlan::getPlanDate, weekStart.plusDays(6));
        vo.setReviewTotalCount(reviewPlanMapper.selectCount(reviewWrapper));
        vo.setReviewFinishedCount(reviewPlanMapper.selectCount(reviewWrapper.clone()
                .eq(ReviewPlan::getStatus, 1)));

        // 各知识点掌握度分布（Mapper XML 分组聚合）
        List<Map<String, Object>> rows = questionMapper.selectKpMastery(userId);
        List<Long> kpIds = rows.stream().map(r -> ((Number) r.get("kpId")).longValue()).toList();
        Map<Long, KnowledgePoint> kpMap = kpIds.isEmpty() ? Map.of()
                : knowledgePointMapper.selectBatchIds(kpIds).stream()
                .collect(Collectors.toMap(KnowledgePoint::getId, Function.identity()));
        List<WeeklyReportVO.KpMastery> kpList = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            WeeklyReportVO.KpMastery km = new WeeklyReportVO.KpMastery();
            Long kpId = ((Number) row.get("kpId")).longValue();
            km.setKnowledgePointId(kpId);
            KnowledgePoint kp = kpMap.get(kpId);
            km.setName(kp == null ? "未知知识点" : kp.getName());
            km.setMastery(Math.round(((Number) row.get("avgMastery")).doubleValue() * 10.0) / 10.0);
            km.setQuestionCount(((Number) row.get("questionCount")).longValue());
            kpList.add(km);
        }
        vo.setKnowledgeMastery(kpList);
        vo.setWeakPoints(kpList.stream()
                .sorted(Comparator.comparingDouble(WeeklyReportVO.KpMastery::getMastery))
                .limit(5)
                .collect(Collectors.toList()));

        // 本周每日新增错题与练习量
        vo.setDailyNewQuestions(fillWeek(weekStart, questionMapper.selectDailyCount(userId, weekStartTime)));
        vo.setDailyPractices(fillWeek(weekStart, practiceRecordMapper.selectDailyCount(userId, weekStartTime)));
        return vo;
    }

    @Override
    public WeeklyReportVO generate() {
        WeeklyReportVO vo = weekly();
        messageService.send(UserContext.getUserId(), "report", "学情周报已生成",
                vo.getWeekStart() + " 开始的本周学情周报已生成：新增错题 " + vo.getNewQuestionCount()
                        + " 道，复习完成 " + vo.getReviewFinishedCount() + "/" + vo.getReviewTotalCount()
                        + "，请前往学情报告页查看。");
        return vo;
    }

    /** 将聚合结果填充为完整 7 天序列（无数据补 0） */
    private List<WeeklyReportVO.DateCount> fillWeek(LocalDate weekStart, List<Map<String, Object>> rows) {
        Map<String, Long> byDate = rows.stream().collect(Collectors.toMap(
                r -> r.get("d").toString(), r -> ((Number) r.get("cnt")).longValue()));
        List<WeeklyReportVO.DateCount> week = new ArrayList<>();
        DateTimeFormatter fmt = DateTimeFormatter.ISO_LOCAL_DATE;
        for (int i = 0; i < 7; i++) {
            String date = weekStart.plusDays(i).format(fmt);
            week.add(new WeeklyReportVO.DateCount(date, byDate.getOrDefault(date, 0L)));
        }
        return week;
    }
}
