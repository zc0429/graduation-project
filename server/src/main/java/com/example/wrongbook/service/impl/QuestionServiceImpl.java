package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.entity.AiAnalysis;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.ReviewPlan;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.AiAnalysisMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.ReviewPlanMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.service.QuestionService;
import com.example.wrongbook.util.FileStorageUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class QuestionServiceImpl implements QuestionService {

    private final QuestionMapper questionMapper;
    private final AiAnalysisMapper aiAnalysisMapper;
    private final VariantQuestionMapper variantQuestionMapper;
    private final ReviewPlanMapper reviewPlanMapper;
    private final FileStorageUtil fileStorageUtil;

    @Override
    public Long create(QuestionRequest request) {
        Question question = new Question();
        question.setUserId(UserContext.getUserId());
        question.setSubjectId(request.getSubjectId());
        question.setStem(request.getStem());
        question.setAnswer(request.getAnswer());
        question.setSource(request.getSource());
        if (StringUtils.hasText(request.getImageBase64())) {
            question.setImageUrl(fileStorageUtil.saveBase64Image(request.getImageBase64()));
        }
        questionMapper.insert(question);
        return question.getId();
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
        return getOwnQuestion(id);
    }

    @Override
    public void update(Long id, QuestionRequest request) {
        Question question = getOwnQuestion(id);
        question.setSubjectId(request.getSubjectId());
        question.setStem(request.getStem());
        question.setAnswer(request.getAnswer());
        question.setSource(request.getSource());
        if (StringUtils.hasText(request.getImageBase64())) {
            question.setImageUrl(fileStorageUtil.saveBase64Image(request.getImageBase64()));
        }
        questionMapper.updateById(question);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void remove(Long id) {
        Question question = getOwnQuestion(id);
        // 级联清理解析、变式题与复习计划（论文 5.4 事务一致性）
        aiAnalysisMapper.delete(new LambdaQueryWrapper<AiAnalysis>()
                .eq(AiAnalysis::getQuestionId, id));
        variantQuestionMapper.delete(new LambdaQueryWrapper<VariantQuestion>()
                .eq(VariantQuestion::getQuestionId, id));
        reviewPlanMapper.delete(new LambdaQueryWrapper<ReviewPlan>()
                .eq(ReviewPlan::getQuestionId, id));
        questionMapper.deleteById(question.getId());
    }

    /** 查询本人错题，不存在或非本人则抛异常（管理员不受限） */
    private Question getOwnQuestion(Long id) {
        Question question = questionMapper.selectById(id);
        if (question == null) {
            throw new BizException("错题不存在");
        }
        if (!"admin".equals(UserContext.getRole()) && !question.getUserId().equals(UserContext.getUserId())) {
            throw new BizException("无权访问该错题");
        }
        return question;
    }
}
