package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 错题表（表 5.4）
 */
@Data
@TableName("question")
public class Question {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 所属学生 */
    private Long userId;

    /** 所属科目 */
    private Long subjectId;

    /** 知识点（AI 归类后回填） */
    private Long knowledgePointId;

    private String stem;

    private String answer;

    /** 题目来源（如作业、试卷） */
    private String source;

    private String imageUrl;

    /** 难度（1-5，AI 评估） */
    private Integer difficulty;

    /** 掌握度（0-100） */
    private Integer mastery;

    /** 题干语义向量（JSON 数组），不向前端返回 */
    @JsonIgnore
    private String embedding;

    /** 状态：1 正常，0 删除（软删除标记） */
    @TableLogic
    @JsonIgnore
    private Integer status;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;
}
