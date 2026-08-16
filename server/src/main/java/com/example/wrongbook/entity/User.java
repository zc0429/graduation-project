package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户表（表 5.1）
 */
@Data
@TableName("user")
public class User {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String username;

    /** 密码（BCrypt 加密存储），不向前端返回 */
    @JsonIgnore
    private String password;

    private String nickname;

    /** 角色：student/teacher/admin */
    private String role;

    private String className;

    private String email;

    /** 状态：1 正常，0 停用（软删除标记） */
    @TableLogic
    @JsonIgnore
    private Integer status;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;
}
