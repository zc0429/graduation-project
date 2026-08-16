package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * AI 解析记录表（表 5.5），与错题一对一
 */
@Data
@TableName("ai_analysis")
public class AiAnalysis {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 对应错题 */
    private Long questionId;

    /** AI 归类知识点 */
    private Long knowledgePointId;

    /** 错因分析 */
    private String errorCause;

    /** 解析内容（analysis 为 MySQL 8 保留字，需反引号） */
    @TableField("`analysis`")
    private String analysis;

    /** 参考的本地题目 ID（JSON） */
    private String referenceIds;

    /** 所用大模型标识 */
    private String llmModel;

    /** 状态：0 生成中，1 成功，2 失败 */
    private Integer status;

    private LocalDateTime createTime;
}
