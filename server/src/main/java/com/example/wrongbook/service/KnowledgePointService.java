package com.example.wrongbook.service;

import com.example.wrongbook.dto.KnowledgePointRequest;
import com.example.wrongbook.vo.KnowledgePointNode;

import java.util.List;

public interface KnowledgePointService {

    /** 知识点树（可按科目过滤） */
    List<KnowledgePointNode> tree(Long subjectId);

    /** 新增知识点（管理员） */
    Long add(KnowledgePointRequest request);

    /** 删除知识点（管理员，物理删除；有子级时拒绝） */
    void remove(Long id);
}
