package com.example.wrongbook.dto;

import lombok.Data;

import java.util.List;

/**
 * 批量分配请求：给用户分配角色、给角色分配权限时提交的 ID 列表
 */
@Data
public class AssignIdsRequest {

    private List<Long> ids;
}
