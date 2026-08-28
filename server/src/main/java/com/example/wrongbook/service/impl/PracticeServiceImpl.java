package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.PracticeRequest;
import com.example.wrongbook.entity.PracticeRecord;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.PracticeRecordMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.service.PracticeService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class PracticeServiceImpl implements PracticeService {

    /** 掌握度增减幅度（论文 5.3 类设计 (7)） */
    private static final int MASTERY_UP = 15;
    private static final int MASTERY_DOWN = 20;

    private final PracticeRecordMapper practiceRecordMapper;
    private final QuestionMapper questionMapper;
    private final VariantQuestionMapper variantQuestionMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long submit(PracticeRequest request) {
        if (request.getIsCorrect() != 0 && request.getIsCorrect() != 1) {
            throw new BizException("作答结果只能为 0 或 1");
        }
        if ((request.getQuestionId() == null) == (request.getVariantId() == null)) {
            throw new BizException("错题与变式题必须且只能选择一项");
        }
        Question question = resolveQuestion(request);
        PracticeRecord record = new PracticeRecord();
        record.setUserId(UserContext.getUserId());
        record.setQuestionId(request.getQuestionId());
        record.setVariantId(request.getVariantId());
        record.setUserAnswer(request.getUserAnswer());
        record.setIsCorrect(request.getIsCorrect());
        record.setDuration(request.getDuration());
        practiceRecordMapper.insert(record);
        // 原子更新掌握度，避免并发练习基于同一个旧值发生丢失更新。
        int delta = request.getIsCorrect() == 1 ? MASTERY_UP : -MASTERY_DOWN;
        int updated = questionMapper.update(null, new LambdaUpdateWrapper<Question>()
                .eq(Question::getId, question.getId())
                .eq(Question::getUserId, UserContext.getUserId())
                .setSql("mastery = LEAST(100, GREATEST(0, mastery + {0}))", delta));
        if (updated != 1) {
            throw new BizException(ResultCode.SERVER_ERROR.getCode(), "掌握度更新失败，请重试");
        }
        return record.getId();
    }

    @Override
    public Page<PracticeRecord> page(Integer pageNum, Integer pageSize) {
        return practiceRecordMapper.selectPage(new Page<>(pageNum, pageSize),
                new LambdaQueryWrapper<PracticeRecord>()
                        .eq(PracticeRecord::getUserId, UserContext.getUserId())
                        .orderByDesc(PracticeRecord::getCreateTime));
    }

    /** 解析作答对象对应的错题并校验归属（变式题回溯原题） */
    private Question resolveQuestion(PracticeRequest request) {
        Long questionId = request.getQuestionId();
        if (questionId == null && request.getVariantId() != null) {
            VariantQuestion variant = variantQuestionMapper.selectById(request.getVariantId());
            if (variant == null) {
                throw new BizException(ResultCode.NOT_FOUND.getCode(), "变式题不存在");
            }
            questionId = variant.getQuestionId();
        }
        if (questionId == null) {
            throw new BizException("作答对象不能为空");
        }
        Question question = questionMapper.selectById(questionId);
        if (question == null) {
            throw new BizException(ResultCode.NOT_FOUND.getCode(), "错题不存在");
        }
        if (!question.getUserId().equals(UserContext.getUserId())) {
            throw new BizException(ResultCode.FORBIDDEN.getCode(), "无权作答该题目");
        }
        return question;
    }
}
