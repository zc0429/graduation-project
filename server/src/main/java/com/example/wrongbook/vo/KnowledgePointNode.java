package com.example.wrongbook.vo;

import lombok.Data;

import java.util.List;

/**
 * 知识点树节点（一级章节 + 二级考点）
 */
@Data
public class KnowledgePointNode {

    private Long id;

    private Long subjectId;

    private String name;

    private List<KnowledgePointNode> children;
}
