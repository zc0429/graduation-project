package com.example.wrongbook.service;

import com.example.wrongbook.entity.Question;
import com.example.wrongbook.vo.ReviewPlanVO;

import java.util.List;

/**
 * 复习计划服务（论文 5.3 类设计 (6)）：依据艾宾浩斯遗忘曲线
 * 设置第 1、2、4、7、15 天共 5 个复习阶段，错题录入当天为第 0 天生成全部阶段计划
 */
public interface ReviewPlanService {

    /** 错题录入后生成全部 5 个阶段的复习计划 */
    void createPlans(Question question);

    /** 今日复习任务（含到期未完成与逾期未完成的，附题干摘要） */
    List<ReviewPlanVO> today();

    /** 完成复习任务（学生仅本人） */
    void finish(Long id);
}
