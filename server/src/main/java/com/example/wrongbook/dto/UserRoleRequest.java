package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class UserRoleRequest {

    @NotNull(message = "用户 ID 不能为空")
    private Long userId;

    @NotNull(message = "角色 ID 不能为空")
    private Long roleId;
}
