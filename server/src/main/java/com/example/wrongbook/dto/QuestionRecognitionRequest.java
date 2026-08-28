package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class QuestionRecognitionRequest {

    @NotBlank(message = "请选择需要识别的题目图片")
    private String imageBase64;
}
