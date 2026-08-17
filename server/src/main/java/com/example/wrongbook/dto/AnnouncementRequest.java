package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class AnnouncementRequest {

    @NotBlank(message = "公告标题不能为空")
    @Size(max = 128, message = "公告标题最长 128 位")
    private String title;

    private String content;
}
