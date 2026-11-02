package com.example.wrongbook.controller;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.AssignIdsRequest;
import com.example.wrongbook.dto.RoleRequest;
import com.example.wrongbook.entity.Role;
import com.example.wrongbook.service.RoleService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 角色管理（实训 RBAC 模块）：角色 CRUD + 给角色分配权限。
 * 类级 @RequireRole("admin") 做角色粗粒度校验，方法级 @SaCheckPermission 做权限码细粒度校验。
 */
@RestController
@RequestMapping("/api/system/role")
@RequiredArgsConstructor
@RequireRole("admin")
public class RoleController {

    private final RoleService roleService;

    @GetMapping("/page")
    @SaCheckPermission("system:role:list")
    public RestResponse<Page<Role>> page(@RequestParam(defaultValue = "1") Integer pageNum,
                                         @RequestParam(defaultValue = "10") Integer pageSize,
                                         @RequestParam(required = false) String keyword) {
        return RestResponse.ok(roleService.page(pageNum, pageSize, keyword));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("system:role:list")
    public RestResponse<Role> get(@PathVariable Long id) {
        return RestResponse.ok(roleService.get(id));
    }

    @PostMapping
    @SaCheckPermission("system:role:add")
    public RestResponse<Long> add(@Validated @RequestBody RoleRequest request) {
        return RestResponse.ok(roleService.add(request));
    }

    @PutMapping("/{id}")
    @SaCheckPermission("system:role:edit")
    public RestResponse<Void> update(@PathVariable Long id, @Validated @RequestBody RoleRequest request) {
        roleService.update(id, request);
        return RestResponse.ok();
    }

    @DeleteMapping("/{id}")
    @SaCheckPermission("system:role:delete")
    public RestResponse<Void> remove(@PathVariable Long id) {
        roleService.remove(id);
        return RestResponse.ok();
    }

    @GetMapping("/{id}/permission-ids")
    @SaCheckPermission("system:role:list")
    public RestResponse<List<Long>> permissionIds(@PathVariable Long id) {
        return RestResponse.ok(roleService.listPermissionIds(id));
    }

    @PutMapping("/{id}/permissions")
    @SaCheckPermission("system:role:edit")
    public RestResponse<Void> assignPermissions(@PathVariable Long id, @RequestBody AssignIdsRequest request) {
        roleService.assignPermissions(id, request.getIds());
        return RestResponse.ok();
    }
}
