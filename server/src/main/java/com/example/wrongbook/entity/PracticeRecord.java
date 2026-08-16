package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 练习记录表（表 5.8）
 */
@Data
@TableName("practice_record")
public class PracticeRecord {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 作答学生 */
    private Long userId;

    /** 重做的错题 */
    private Long questionId;

    /** 作答的变式题 */
    private Long variantId;

    private String userAnswer;

    /** 是否正确：1 正确，0 错误 */
    private Integer isCorrect;

    /** 作答用时（秒） */
    private Integer duration;

    private LocalDateTime createTime;
}
