package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.ReviewPlan;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.ReviewPlanMapper;
import com.example.wrongbook.service.ReviewPlanService;
import com.example.wrongbook.vo.ReviewPlanVO;
import com.example.wrongbook.util.QuestionContent;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ReviewPlanServiceImpl implements ReviewPlanService {

    /** 艾宾浩斯遗忘曲线复习节点（第 1/2/4/7/15 天，论文 5.3 类设计 (6)） */
    private static final int[] REVIEW_DAYS = {1, 2, 4, 7, 15};

    private final ReviewPlanMapper reviewPlanMapper;
    private final QuestionMapper questionMapper;

    @Override
    public void createPlans(Question question) {
        LocalDate base = LocalDate.now();
        for (int i = 0; i < REVIEW_DAYS.length; i++) {
            ReviewPlan plan = new ReviewPlan();
            plan.setUserId(question.getUserId());
            plan.setQuestionId(question.getId());
            plan.setReviewStage(i + 1);
            plan.setPlanDate(base.plusDays(REVIEW_DAYS[i]));
            reviewPlanMapper.insert(plan);
        }
    }

    @Override
    public List<ReviewPlanVO> today() {
        LambdaQueryWrapper<ReviewPlan> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(ReviewPlan::getUserId, UserContext.getUserId())
                .le(ReviewPlan::getPlanDate, LocalDate.now())
                .ne(ReviewPlan::getStatus, 1)
                .orderByAsc(ReviewPlan::getPlanDate)
                .orderByAsc(ReviewPlan::getReviewStage);
        List<ReviewPlan> plans = reviewPlanMapper.selectList(wrapper);
        if (plans.isEmpty()) {
            return List.of();
        }
        Map<Long, Question> questionMap = questionMapper.selectBatchIds(
                        plans.stream().map(ReviewPlan::getQuestionId).distinct().toList())
                .stream().collect(Collectors.toMap(Question::getId, q -> q));
        return plans.stream().map(plan -> {
            ReviewPlanVO vo = new ReviewPlanVO();
            vo.setId(plan.getId());
            vo.setQuestionId(plan.getQuestionId());
            vo.setReviewStage(plan.getReviewStage());
            vo.setPlanDate(plan.getPlanDate());
            vo.setStatus(plan.getStatus());
            Question q = questionMap.get(plan.getQuestionId());
            if (q != null) {
                vo.setSubjectId(q.getSubjectId());
                vo.setMastery(q.getMastery());
                String stem = QuestionContent.plainText(q.getStem());
                vo.setStemSummary(stem.length() > 60 ? stem.substring(0, 60) + "…" : stem);
            }
            return vo;
        }).collect(Collectors.toList());
    }

    @Override
    public void finish(Long id) {
        ReviewPlan plan = reviewPlanMapper.selectById(id);
        if (plan == null) {
            throw new BizException(ResultCode.NOT_FOUND.getCode(), "复习任务不存在");
        }
        if (!plan.getUserId().equals(UserContext.getUserId())) {
            throw new BizException(ResultCode.FORBIDDEN.getCode(), "无权操作该复习任务");
        }
        if (plan.getStatus() == 1) {
            throw new BizException("该复习任务已完成");
        }
        plan.setStatus(1);
        plan.setFinishTime(LocalDateTime.now());
        reviewPlanMapper.updateById(plan);
    }
}
