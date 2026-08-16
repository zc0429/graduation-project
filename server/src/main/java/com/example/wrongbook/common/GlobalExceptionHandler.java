package com.example.wrongbook.common;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

/**
 * 全局异常处理：统一转为 {code, message, data} 响应
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BizException.class)
    public RestResponse<Void> handleBiz(BizException e) {
        log.warn("业务异常：{}", e.getMessage());
        return RestResponse.error(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(BindException.class)
    public RestResponse<Void> handleBind(BindException e) {
        FieldError fieldError = e.getBindingResult().getFieldError();
        String message = fieldError != null ? fieldError.getDefaultMessage() : ResultCode.BAD_REQUEST.getMessage();
        return RestResponse.error(ResultCode.BAD_REQUEST.getCode(), message);
    }

    @ExceptionHandler({MissingServletRequestParameterException.class,
            MethodArgumentTypeMismatchException.class, HttpMessageNotReadableException.class})
    public RestResponse<Void> handleBadRequest(Exception e) {
        log.warn("请求参数异常：{}", e.getMessage());
        return RestResponse.error(ResultCode.BAD_REQUEST);
    }

    @ExceptionHandler(NoResourceFoundException.class)
    public RestResponse<Void> handleNotFound(NoResourceFoundException e) {
        return RestResponse.error(ResultCode.NOT_FOUND);
    }

    @ExceptionHandler(Exception.class)
    public RestResponse<Void> handleException(Exception e) {
        log.error("服务器异常", e);
        return RestResponse.error(ResultCode.SERVER_ERROR);
    }
}
