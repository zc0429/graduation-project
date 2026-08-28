package com.example.wrongbook.common;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
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
    public ResponseEntity<RestResponse<Void>> handleBiz(BizException e) {
        log.warn("业务异常：{}", e.getMessage());
        return response(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(BindException.class)
    public ResponseEntity<RestResponse<Void>> handleBind(BindException e) {
        FieldError fieldError = e.getBindingResult().getFieldError();
        String message = fieldError != null ? fieldError.getDefaultMessage() : ResultCode.BAD_REQUEST.getMessage();
        return response(ResultCode.BAD_REQUEST.getCode(), message);
    }

    @ExceptionHandler({MissingServletRequestParameterException.class,
            MethodArgumentTypeMismatchException.class, HttpMessageNotReadableException.class})
    public ResponseEntity<RestResponse<Void>> handleBadRequest(Exception e) {
        log.warn("请求参数异常：{}", e.getMessage());
        return response(ResultCode.BAD_REQUEST);
    }

    @ExceptionHandler(NoResourceFoundException.class)
    public ResponseEntity<RestResponse<Void>> handleNotFound(NoResourceFoundException e) {
        return response(ResultCode.NOT_FOUND);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<RestResponse<Void>> handleException(Exception e) {
        log.error("服务器异常", e);
        return response(ResultCode.SERVER_ERROR);
    }

    private ResponseEntity<RestResponse<Void>> response(ResultCode resultCode) {
        return response(resultCode.getCode(), resultCode.getMessage());
    }

    private ResponseEntity<RestResponse<Void>> response(Integer code, String message) {
        HttpStatus status = HttpStatus.resolve(code);
        if (status == null) {
            status = HttpStatus.BAD_REQUEST;
        }
        return ResponseEntity.status(status).body(RestResponse.error(code, message));
    }
}
