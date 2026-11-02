package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 角色表（实训 RBAC 权限模块：user / role / permission / user_role / role_permission 五表之一）
 * 与 user.role 字段对应：role_key 取值 student / teacher / admin。
 */
@Data
@TableName("role")
public class Role {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 角色名称（如 管理员） */
    private String roleName;

    /** 角色标识（如 admin），唯一 */
    private String roleKey;

    /** 排序号 */
    private Integer sort;

    /** 状态：1 正常，0 停用 */
    private Integer status;

    /** 备注 */
    private String remark;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;
}
