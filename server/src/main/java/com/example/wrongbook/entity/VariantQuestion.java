package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 变式题表（表 5.6）
 */
@Data
@TableName("variant_question")
public class VariantQuestion {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 原题 ID */
    private Long questionId;

    private String stem;

    private String answer;

    /** 难度（1-5） */
    private Integer difficulty;

    private LocalDateTime createTime;
}
