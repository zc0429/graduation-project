package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class KnowledgePointRequest {

    @NotNull(message = "所属科目不能为空")
    private Long subjectId;

    /** 父级 ID：0 表示一级章节 */
    @NotNull(message = "父级 ID 不能为空")
    private Long parentId;

    @NotBlank(message = "知识点名称不能为空")
    @Size(max = 64, message = "知识点名称最长 64 位")
    private String name;

    private Integer sort;
}
