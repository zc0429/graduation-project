package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 科目表（表 5.2）
 */
@Data
@TableName("subject")
public class Subject {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String code;

    private Integer sort;

    /** 状态：1 启用，0 停用（软删除标记） */
    @TableLogic
    @JsonIgnore
    private Integer status;

    private LocalDateTime createTime;
}
