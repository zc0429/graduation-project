package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 知识点表（表 5.3），parent_id=0 表示一级章节
 */
@Data
@TableName("knowledge_point")
public class KnowledgePoint {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 所属科目 */
    private Long subjectId;

    /** 父级 ID：0 表示一级章节 */
    private Long parentId;

    private String name;

    private Integer sort;

    private LocalDateTime createTime;
}
