package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class RolePermissionRequest {

    @NotNull(message = "角色 ID 不能为空")
    private Long roleId;

    @NotNull(message = "权限 ID 不能为空")
    private Long permissionId;
}
