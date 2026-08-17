package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class QuestionRequest {

    @NotNull(message = "所属科目不能为空")
    private Long subjectId;

    @NotBlank(message = "题干不能为空")
    private String stem;

    private String answer;

    private String source;

    /** 题目图片（Base64，由录入/修改接口一并接收，服务端落盘本地） */
    private String imageBase64;
}
