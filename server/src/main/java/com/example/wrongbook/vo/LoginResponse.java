package com.example.wrongbook.vo;

import com.example.wrongbook.entity.User;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class LoginResponse {

    private String token;

    private User user;
}
