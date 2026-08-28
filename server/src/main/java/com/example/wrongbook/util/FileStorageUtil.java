package com.example.wrongbook.util;

import com.example.wrongbook.common.BizException;
import lombok.extern.slf4j.Slf4j;
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
@Slf4j
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

    /** 图片路径是否为本系统上传路径 */
    public boolean isUploadPath(String imageUrl) {
        return StringUtils.hasText(imageUrl) && imageUrl.startsWith("/uploads/");
    }

    /** 读取本人错题详情时以内联 Data URI 返回，避免上传目录匿名暴露。 */
    public String readAsDataUrl(String imageUrl) {
        Path path = resolveUploadPath(imageUrl);
        try {
            byte[] bytes = Files.readAllBytes(path);
            return "data:" + mimeType(path) + ";base64," + Base64.getEncoder().encodeToString(bytes);
        } catch (IOException e) {
            log.warn("题目图片读取失败：errorType={}", e.getClass().getSimpleName());
            return null;
        }
    }

    /** 替换或删除错题后的旧文件清理；失败不回滚已经成功的业务事务。 */
    public void deleteIfExists(String imageUrl) {
        if (!isUploadPath(imageUrl)) {
            return;
        }
        try {
            Files.deleteIfExists(resolveUploadPath(imageUrl));
        } catch (IOException | BizException e) {
            log.warn("旧题图清理失败：errorType={}", e.getClass().getSimpleName());
        }
    }

    private Path resolveUploadPath(String imageUrl) {
        if (!isUploadPath(imageUrl)) {
            throw new BizException("题目图片路径无效");
        }
        Path root = Paths.get(uploadDir).toAbsolutePath().normalize();
        String relative = imageUrl.substring("/uploads/".length());
        Path resolved = root.resolve(relative).normalize();
        if (!resolved.startsWith(root)) {
            throw new BizException("题目图片路径无效");
        }
        return resolved;
    }

    private String mimeType(Path path) {
        String name = path.getFileName().toString().toLowerCase();
        if (name.endsWith(".jpg") || name.endsWith(".jpeg")) {
            return "image/jpeg";
        }
        if (name.endsWith(".gif")) {
            return "image/gif";
        }
        if (name.endsWith(".webp")) {
            return "image/webp";
        }
        return "image/png";
    }
}
