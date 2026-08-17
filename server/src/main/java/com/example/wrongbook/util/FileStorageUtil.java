package com.example.wrongbook.util;

import com.example.wrongbook.common.BizException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Base64;
import java.util.UUID;

/**
 * 错题图片本地存储：Base64 解码后按日期分目录落盘，返回访问路径
 */
@Component
public class FileStorageUtil {

    private static final long MAX_SIZE = 10 * 1024 * 1024L;

    @Value("${app.upload-dir}")
    private String uploadDir;

    /**
     * 保存 Base64 图片，返回 /uploads/yyyy-MM-dd/xxx.ext 形式的访问路径
     *
     * @param base64 支持 "data:image/png;base64,..." 或纯 Base64 串
     */
    public String saveBase64Image(String base64) {
        String ext = ".png";
        String data = base64;
        if (base64.startsWith("data:")) {
            int comma = base64.indexOf(',');
            if (comma < 0) {
                throw new BizException("图片数据格式不正确");
            }
            String mime = base64.substring(5, base64.indexOf(';'));
            ext = switch (mime) {
                case "image/jpeg" -> ".jpg";
                case "image/gif" -> ".gif";
                case "image/webp" -> ".webp";
                default -> ".png";
            };
            data = base64.substring(comma + 1);
        }
        byte[] bytes;
        try {
            bytes = Base64.getDecoder().decode(data);
        } catch (IllegalArgumentException e) {
            throw new BizException("图片 Base64 解码失败");
        }
        if (bytes.length > MAX_SIZE) {
            throw new BizException("图片大小不能超过 10MB");
        }
        String dateDir = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        String fileName = UUID.randomUUID().toString().replace("-", "") + ext;
        Path dir = Paths.get(uploadDir).toAbsolutePath().resolve(dateDir);
        try {
            Files.createDirectories(dir);
            Files.write(dir.resolve(fileName), bytes);
        } catch (IOException e) {
            throw new BizException("图片保存失败");
        }
        return "/uploads/" + dateDir + "/" + fileName;
    }

    /** 解析上传目录的绝对路径（供静态资源映射使用） */
    public String resolveUploadDir() {
        return Paths.get(uploadDir).toAbsolutePath().toString();
    }

    /** 图片路径是否为本系统上传路径 */
    public boolean isUploadPath(String imageUrl) {
        return StringUtils.hasText(imageUrl) && imageUrl.startsWith("/uploads/");
    }
}
