package com.example.wrongbook.controller;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.PermissionRequest;
import com.example.wrongbook.entity.Permission;
import com.example.wrongbook.service.PermissionService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 权限管理（实训 RBAC 模块）：权限 CRUD，权限以扁平列表返回，前端按 parentId 组装树。
 */
@RestController
@RequestMapping("/api/system/permission")
@RequiredArgsConstructor
@RequireRole("admin")
public class PermissionController {

    private final PermissionService permissionService;

    @GetMapping("/list")
    @SaCheckPermission("system:permission:list")
    public RestResponse<List<Permission>> list() {
        return RestResponse.ok(permissionService.list());
    }

    @GetMapping("/{id}")
    @SaCheckPermission("system:permission:list")
    public RestResponse<Permission> get(@PathVariable Long id) {
        return RestResponse.ok(permissionService.get(id));
    }

    @PostMapping
    @SaCheckPermission("system:permission:add")
    public RestResponse<Long> add(@Validated @RequestBody PermissionRequest request) {
        return RestResponse.ok(permissionService.add(request));
    }

    @PutMapping("/{id}")
    @SaCheckPermission("system:permission:edit")
    public RestResponse<Void> update(@PathVariable Long id, @Validated @RequestBody PermissionRequest request) {
        permissionService.update(id, request);
        return RestResponse.ok();
    }

    @DeleteMapping("/{id}")
    @SaCheckPermission("system:permission:delete")
    public RestResponse<Void> remove(@PathVariable Long id) {
        permissionService.remove(id);
        return RestResponse.ok();
    }
}
