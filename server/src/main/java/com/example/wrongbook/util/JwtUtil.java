package com.example.wrongbook.util;

/**
 * 【已下线】原 JWT 工具类。
 *
 * <p>实训改造后，登录会话与权限校验统一由 Sa-Token 承担
 * （登录见 AuthServiceImpl 的 StpUtil.login，会话校验见 AuthInterceptor，
 * 权限码数据源见 StpInterfaceImpl），本类不再被任何代码引用，
 * 仅保留此类文件说明技术迁移过程，请勿再使用。</p>
 *
 * @deprecated 已由 Sa-Token 替代
 */
@Deprecated
public final class JwtUtil {

    private JwtUtil() {
    }
}
