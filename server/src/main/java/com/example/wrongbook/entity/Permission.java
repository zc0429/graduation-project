package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 权限表（实训 RBAC 权限模块五表之一）
 * permission_key 为 Sa-Token 校验用的权限码，如 system:role:add、business:question:list。
 */
@Data
@TableName("permission")
public class Permission {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 父级权限 ID：0 表示一级（模块） */
    private Long parentId;

    /** 权限名称（如 角色管理、新增错题） */
    private String name;

    /** 权限码，唯一，如 system:user:list */
    private String permissionKey;

    /** 类型：menu 菜单 / button 按钮（操作） */
    private String type;

    /** 前端路由路径（菜单类权限使用） */
    private String path;

    /** 排序号 */
    private Integer sort;

    /** 状态：1 正常，0 停用 */
    private Integer status;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;
}
