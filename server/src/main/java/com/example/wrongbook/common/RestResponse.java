package com.example.wrongbook.common;

import lombok.Data;

import java.io.Serializable;

/**
 * 统一响应封装：{code, message, data}，code 为 0 表示成功
 */
@Data
public class RestResponse<T> implements Serializable {

    private Integer code;
    private String message;
    private T data;

    public static <T> RestResponse<T> ok(T data) {
        RestResponse<T> r = new RestResponse<>();
        r.setCode(ResultCode.SUCCESS.getCode());
        r.setMessage(ResultCode.SUCCESS.getMessage());
        r.setData(data);
        return r;
    }

    public static <T> RestResponse<T> ok() {
        return ok(null);
    }

    public static <T> RestResponse<T> error(Integer code, String message) {
        RestResponse<T> r = new RestResponse<>();
        r.setCode(code);
        r.setMessage(message);
        return r;
    }

    public static <T> RestResponse<T> error(ResultCode resultCode) {
        return error(resultCode.getCode(), resultCode.getMessage());
    }
}
