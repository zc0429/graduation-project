package com.example.wrongbook.common;

import lombok.Getter;

/**
 * 业务异常：由全局异常处理器转为统一响应
 */
@Getter
public class BizException extends RuntimeException {

    private final Integer code;

    public BizException(String message) {
        this(ResultCode.BAD_REQUEST.getCode(), message);
    }

    public BizException(ResultCode resultCode) {
        this(resultCode.getCode(), resultCode.getMessage());
    }

    public BizException(Integer code, String message) {
        super(message);
        this.code = code;
    }
}
