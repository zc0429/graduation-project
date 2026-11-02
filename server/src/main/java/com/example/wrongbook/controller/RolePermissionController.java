package com.example.wrongbook.controller;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.RolePermissionRequest;
import com.example.wrongbook.entity.RolePermission;
import com.example.wrongbook.service.RolePermissionService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * 角色-权限关联管理（实训 RBAC 模块）：关联的分页查询、新增与删除。
 * 批量分配走 RoleController 的 PUT /api/system/role/{id}/permissions。
 */
@RestController
@RequestMapping("/api/system/role-permission")
@RequiredArgsConstructor
@RequireRole("admin")
public class RolePermissionController {

    private final RolePermissionService rolePermissionService;

    @GetMapping("/page")
    @SaCheckPermission("system:role:list")
    public RestResponse<Page<RolePermission>> page(@RequestParam(defaultValue = "1") Integer pageNum,
                                                   @RequestParam(defaultValue = "10") Integer pageSize,
                                                   @RequestParam(required = false) Long roleId,
                                                   @RequestParam(required = false) Long permissionId) {
        return RestResponse.ok(rolePermissionService.page(pageNum, pageSize, roleId, permissionId));
    }

    @PostMapping
    @SaCheckPermission("system:role:edit")
    public RestResponse<Long> add(@Validated @RequestBody RolePermissionRequest request) {
        return RestResponse.ok(rolePermissionService.add(request));
    }

    @DeleteMapping("/{id}")
    @SaCheckPermission("system:role:edit")
    public RestResponse<Void> remove(@PathVariable Long id) {
        rolePermissionService.remove(id);
        return RestResponse.ok();
    }
}
