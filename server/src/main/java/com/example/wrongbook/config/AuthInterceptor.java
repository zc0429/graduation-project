package com.example.wrongbook.config;

import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.common.UserContext;
import cn.dev33.satoken.stp.StpUtil;
import com.example.wrongbook.entity.User;
import com.example.wrongbook.mapper.UserMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Map;

/**
 * 鉴权拦截器：用 Sa-Token 会话校验登录态并写入 UserContext，再按 @RequireRole 校验角色。
 * 实训改造：原 JWT 解析已切换为 Sa-Token（token 仍经 Authorization: Bearer 传递，前端无需改动）；
 * 细粒度权限码校验由 Sa-Token 的 @SaCheckPermission 注解（SaInterceptor）负责，数据源见 StpInterfaceImpl。
 */
@Component
@RequiredArgsConstructor
public class AuthInterceptor implements HandlerInterceptor {

    private final UserMapper userMapper;
    private final ObjectMapper objectMapper;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws IOException {
        if (!(handler instanceof HandlerMethod handlerMethod)) {
            return true;
        }
        String header = request.getHeader("Authorization");
        Long loginId = null;
        if (header != null && header.startsWith("Bearer ")) {
            Object id = StpUtil.getLoginIdByToken(header.substring(7));
            if (id != null) {
                try {
                    loginId = Long.valueOf(String.valueOf(id));
                } catch (NumberFormatException ignored) {
                    loginId = null;
                }
            }
        }
        if (loginId == null) {
            writeError(response, ResultCode.UNAUTHORIZED);
            return false;
        }
        User currentUser = userMapper.selectById(loginId);
        if (currentUser == null || !Integer.valueOf(1).equals(currentUser.getStatus())) {
            writeError(response, ResultCode.UNAUTHORIZED);
            return false;
        }
        LoginUser user = new LoginUser(currentUser.getId(), currentUser.getRole());
        // 角色校验：方法注解优先于类注解
        RequireRole requireRole = handlerMethod.getMethodAnnotation(RequireRole.class);
        if (requireRole == null) {
            requireRole = handlerMethod.getBeanType().getAnnotation(RequireRole.class);
        }
        if (requireRole != null && Arrays.stream(requireRole.value()).noneMatch(user.getRole()::equals)) {
            writeError(response, ResultCode.FORBIDDEN);
            return false;
        }
        UserContext.set(user);
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        UserContext.clear();
    }

    private void writeError(HttpServletResponse response, ResultCode resultCode) throws IOException {
        response.setStatus(resultCode.getCode());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.getWriter().write(objectMapper.writeValueAsString(
                Map.of("code", resultCode.getCode(), "message", resultCode.getMessage())));
    }
}
