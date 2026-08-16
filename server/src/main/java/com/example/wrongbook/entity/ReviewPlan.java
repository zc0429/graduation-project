package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 复习计划表（表 5.7）
 */
@Data
@TableName("review_plan")
public class ReviewPlan {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 所属学生 */
    private Long userId;

    /** 待复习错题 */
    private Long questionId;

    /** 复习阶段（第 1-5 次） */
    private Integer reviewStage;

    /** 计划复习日期 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate planDate;

    /** 状态：0 待复习，1 已完成，2 已过期 */
    private Integer status;

    private LocalDateTime finishTime;

    private LocalDateTime createTime;
}
