package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("learning_content")
public class LearningContent {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long questionId;
    private Long knowledgePointId;
    private String inputHash;
    private String content;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
