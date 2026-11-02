package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class PermissionRequest {

    /** 父级权限 ID：0 表示一级 */
    private Long parentId;

    @NotBlank(message = "权限名称不能为空")
    @Size(max = 64, message = "权限名称最长 64 位")
    private String name;

    @NotBlank(message = "权限码不能为空")
    @Size(max = 64, message = "权限码最长 64 位")
    private String permissionKey;

    /** 类型：menu 菜单 / button 按钮 */
    @Size(max = 16, message = "类型最长 16 位")
    private String type;

    @Size(max = 128, message = "路由路径最长 128 位")
    private String path;

    private Integer sort;

    /** 状态：1 正常，0 停用；不传默认 1 */
    private Integer status;
}
