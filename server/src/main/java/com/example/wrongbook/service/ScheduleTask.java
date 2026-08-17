package com.example.wrongbook.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.ReviewPlan;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.ReviewPlanMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 定时任务（论文 5.3 类设计 (9)）：
 * 每日扫描复习计划表，到期提醒并置逾期状态；每周一生成学情周报提醒
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ScheduleTask {

    private final ReviewPlanMapper reviewPlanMapper;
    private final QuestionMapper questionMapper;
    private final MessageService messageService;

    /** 每日 08:00：逾期计划置为已过期；今日待复习按用户聚合发送提醒 */
    @Scheduled(cron = "0 0 8 * * ?")
    public void reviewReminder() {
        LocalDate today = LocalDate.now();
        int expired = reviewPlanMapper.update(null, new LambdaUpdateWrapper<ReviewPlan>()
                .set(ReviewPlan::getStatus, 2)
                .lt(ReviewPlan::getPlanDate, today)
                .eq(ReviewPlan::getStatus, 0));
        List<ReviewPlan> todayPlans = reviewPlanMapper.selectList(new LambdaQueryWrapper<ReviewPlan>()
                .eq(ReviewPlan::getPlanDate, today)
                .eq(ReviewPlan::getStatus, 0));
        Map<Long, Long> byUser = todayPlans.stream()
                .collect(Collectors.groupingBy(ReviewPlan::getUserId, Collectors.counting()));
        byUser.forEach((userId, count) -> messageService.send(userId, "review_remind",
                "今日复习提醒", "今日有 " + count + " 道错题到期待复习，请前往复习计划页完成。"));
        log.info("复习提醒任务完成：逾期 {} 条，提醒 {} 人", expired, byUser.size());
    }

    /** 每周一 09:00：给有错题的学生发送周报生成通知 */
    @Scheduled(cron = "0 0 9 ? * MON")
    public void weeklyReport() {
        List<Long> userIds = questionMapper.selectObjs(new LambdaQueryWrapper<Question>()
                        .select(Question::getUserId)
                        .groupBy(Question::getUserId))
                .stream().map(o -> ((Number) o).longValue()).toList();
        userIds.forEach(userId -> messageService.send(userId, "report",
                "学情周报已生成", "本周学情周报已生成，请前往学情报告页查看薄弱知识点与掌握度趋势。"));
        log.info("学情周报任务完成：通知 {} 人", userIds.size());
    }
}
