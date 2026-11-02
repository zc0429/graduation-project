package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RoleRequest {

    @NotBlank(message = "角色名称不能为空")
    @Size(max = 32, message = "角色名称最长 32 位")
    private String roleName;

    @NotBlank(message = "角色标识不能为空")
    @Size(max = 32, message = "角色标识最长 32 位")
    private String roleKey;

    private Integer sort;

    /** 状态：1 正常，0 停用；不传默认 1 */
    private Integer status;

    @Size(max = 255, message = "备注最长 255 位")
    private String remark;
}
