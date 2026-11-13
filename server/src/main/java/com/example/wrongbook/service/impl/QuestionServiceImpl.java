package com.example.wrongbook.service.impl;

import com.alibaba.excel.EasyExcel;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.entity.AiAnalysis;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.LearningContent;
import com.example.wrongbook.mapper.LearningContentMapper;
import com.example.wrongbook.entity.ReviewPlan;
import com.example.wrongbook.entity.Subject;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.AiAnalysisMapper;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.ReviewPlanMapper;
import com.example.wrongbook.mapper.SubjectMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.service.QuestionService;
import com.example.wrongbook.service.ReviewPlanService;
import com.example.wrongbook.util.FileStorageUtil;
import com.example.wrongbook.vo.QuestionExportRow;
import com.example.wrongbook.util.QuestionContent;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class QuestionServiceImpl implements QuestionService {

    private final QuestionMapper questionMapper;
    private final AiAnalysisMapper aiAnalysisMapper;
    private final VariantQuestionMapper variantQuestionMapper;
    private final LearningContentMapper learningContentMapper;
    private final ReviewPlanMapper reviewPlanMapper;
    private final SubjectMapper subjectMapper;
    private final KnowledgePointMapper knowledgePointMapper;
    private final ReviewPlanService reviewPlanService;
    private final FileStorageUtil fileStorageUtil;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long create(QuestionRequest request) {
        Question question = new Question();
        question.setUserId(UserContext.getUserId());
        question.setSubjectId(requireSubject(request.getSubjectId()));
        question.setStem(QuestionContent.validatedStem(request.getStem()));
        question.setAnswer(request.getAnswer());
        question.setSource(request.getSource());
        String savedImageUrl = null;
        try {
            if (StringUtils.hasText(request.getImageBase64())) {
                savedImageUrl = fileStorageUtil.saveBase64Image(request.getImageBase64());
                question.setImageUrl(savedImageUrl);
            }
            questionMapper.insert(question);
            // 录入成功建立固定第 1/2/4/7/15 天复习计划，不动态估计遗忘曲线。
            reviewPlanService.createPlans(question);
            return question.getId();
        } catch (RuntimeException e) {
            fileStorageUtil.deleteIfExists(savedImageUrl);
            throw e;
        }
    }

    @Override
    public Page<Question> page(Integer pageNum, Integer pageSize, Long subjectId, Long knowledgePointId) {
        LambdaQueryWrapper<Question> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Question::getUserId, UserContext.getUserId())
                .eq(subjectId != null, Question::getSubjectId, subjectId)
                .eq(knowledgePointId != null, Question::getKnowledgePointId, knowledgePointId)
                .orderByDesc(Question::getCreateTime);
        return questionMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
    }

    @Override
    public Question detail(Long id) {
        Question question = getOwnQuestion(id);
        if (fileStorageUtil.isUploadPath(question.getImageUrl())) {
            question.setImageUrl(fileStorageUtil.readAsDataUrl(question.getImageUrl()));
        }
        return question;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void update(Long id, QuestionRequest request) {
        Question question = getOwnQuestion(id);
        requireSubject(request.getSubjectId());
        String stem = QuestionContent.validatedStem(request.getStem());
        boolean aiInputChanged = !Objects.equals(question.getSubjectId(), request.getSubjectId())
                || !Objects.equals(question.getStem(), stem)
                || !Objects.equals(question.getAnswer(), request.getAnswer());
        LambdaUpdateWrapper<Question> update = new LambdaUpdateWrapper<Question>()
                .eq(Question::getId, id)
                .set(Question::getSubjectId, request.getSubjectId())
                .set(Question::getStem, stem)
                .set(Question::getAnswer, request.getAnswer())
                .set(Question::getSource, request.getSource());
        String replacementImageUrl = null;
        if (StringUtils.hasText(request.getImageBase64())) {
            replacementImageUrl = fileStorageUtil.saveBase64Image(request.getImageBase64());
            update.set(Question::getImageUrl, replacementImageUrl);
        }
        if (aiInputChanged) {
            update.set(Question::getEmbedding, null)
                    .set(Question::getKnowledgePointId, null)
                    .set(Question::getDifficulty, null);
        }
        try {
            questionMapper.update(null, update);
            if (aiInputChanged) {
                learningContentMapper.delete(new LambdaQueryWrapper<LearningContent>().eq(LearningContent::getQuestionId, question.getId()));
                aiAnalysisMapper.delete(new LambdaQueryWrapper<AiAnalysis>()
                        .eq(AiAnalysis::getQuestionId, id));
                variantQuestionMapper.delete(new LambdaQueryWrapper<VariantQuestion>()
                        .eq(VariantQuestion::getQuestionId, id));
            }
        } catch (RuntimeException e) {
            fileStorageUtil.deleteIfExists(replacementImageUrl);
            throw e;
        }
        if (replacementImageUrl != null && !replacementImageUrl.equals(question.getImageUrl())) {
            fileStorageUtil.deleteIfExists(question.getImageUrl());
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void remove(Long id) {
        Question question = getOwnQuestion(id);
        // 级联清理解析、变式题与复习计划（论文 5.4 事务一致性）
        learningContentMapper.delete(new LambdaQueryWrapper<LearningContent>().eq(LearningContent::getQuestionId, question.getId()));
        aiAnalysisMapper.delete(new LambdaQueryWrapper<AiAnalysis>()
                .eq(AiAnalysis::getQuestionId, id));
        variantQuestionMapper.delete(new LambdaQueryWrapper<VariantQuestion>()
                .eq(VariantQuestion::getQuestionId, id));
        reviewPlanMapper.delete(new LambdaQueryWrapper<ReviewPlan>()
                .eq(ReviewPlan::getQuestionId, id));
        questionMapper.deleteById(question.getId());
        fileStorageUtil.deleteIfExists(question.getImageUrl());
    }

    private Long requireSubject(Long subjectId) {
        if (subjectId == null || subjectMapper.selectById(subjectId) == null) {
            throw new BizException("所属科目不存在或已停用");
        }
        return subjectId;
    }

    /** 查询本人错题；管理员内部调用可处理学生数据，HTTP 学生接口另有角色限制。 */
    private Question getOwnQuestion(Long id) {
        Question question = questionMapper.selectById(id);
        if (question == null) {
            throw new BizException(ResultCode.NOT_FOUND.getCode(), "错题不存在");
        }
        if (!"admin".equals(UserContext.getRole()) && !question.getUserId().equals(UserContext.getUserId())) {
            throw new BizException(ResultCode.FORBIDDEN.getCode(), "无权访问该错题");
        }
        return question;
    }

    @Override
    public void export(Long subjectId, Long knowledgePointId, HttpServletResponse response) {
        List<Question> list = questionMapper.selectList(new LambdaQueryWrapper<Question>()
                .eq(Question::getUserId, UserContext.getUserId())
                .eq(subjectId != null, Question::getSubjectId, subjectId)
                .eq(knowledgePointId != null, Question::getKnowledgePointId, knowledgePointId)
                .orderByAsc(Question::getCreateTime));
        Map<Long, Subject> subjectMap = subjectMapper.selectList(null).stream()
                .collect(Collectors.toMap(Subject::getId, Function.identity()));
        Map<Long, KnowledgePoint> kpMap = knowledgePointMapper.selectList(null).stream()
                .collect(Collectors.toMap(KnowledgePoint::getId, Function.identity()));
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        List<QuestionExportRow> rows = list.stream().map(q -> {
            QuestionExportRow row = new QuestionExportRow();
            row.setStem(QuestionContent.plainText(q.getStem()));
            row.setAnswer(q.getAnswer());
            Subject subject = subjectMap.get(q.getSubjectId());
            row.setSubjectName(subject == null ? "" : subject.getName());
            KnowledgePoint kp = q.getKnowledgePointId() == null ? null : kpMap.get(q.getKnowledgePointId());
            row.setKnowledgePointName(kp == null ? "未归类" : kp.getName());
            row.setDifficulty(q.getDifficulty());
            row.setMastery(q.getMastery());
            row.setSource(q.getSource());
            row.setCreateTime(q.getCreateTime() == null ? "" : q.getCreateTime().format(fmt));
            return row;
        }).collect(Collectors.toList());
        try {
            response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
            response.setCharacterEncoding(StandardCharsets.UTF_8.name());
            String fileName = URLEncoder.encode("错题本.xlsx", StandardCharsets.UTF_8);
            response.setHeader("Content-Disposition", "attachment;filename*=UTF-8''" + fileName);
            EasyExcel.write(response.getOutputStream(), QuestionExportRow.class)
                    .sheet("错题本")
                    .doWrite(rows);
        } catch (IOException e) {
            throw new BizException("导出失败");
        }
    }
}
