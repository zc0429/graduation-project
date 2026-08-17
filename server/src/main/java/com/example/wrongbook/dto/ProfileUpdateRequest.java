package com.example.wrongbook.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ProfileUpdateRequest {

    @Size(max = 32, message = "昵称最长 32 位")
    private String nickname;

    @Email(message = "邮箱格式不正确")
    private String email;

    @Size(max = 64, message = "班级名称最长 64 位")
    private String className;
}
