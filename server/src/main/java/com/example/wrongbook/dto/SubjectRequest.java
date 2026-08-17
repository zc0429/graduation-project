package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class SubjectRequest {

    @NotBlank(message = "科目名称不能为空")
    @Size(max = 32, message = "科目名称最长 32 位")
    private String name;

    @Size(max = 32, message = "科目编码最长 32 位")
    private String code;

    private Integer sort;
}
