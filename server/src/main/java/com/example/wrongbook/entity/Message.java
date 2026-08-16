package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 消息通知表（补充表，对应接口表 5.9 消息通知管理）
 */
@Data
@TableName("message")
public class Message {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 接收用户 */
    private Long userId;

    /** 消息类型：review_remind 复习提醒/report 报告/system 系统 */
    private String type;

    private String title;

    private String content;

    /** 是否已读：1 已读，0 未读 */
    private Integer isRead;

    private LocalDateTime createTime;
}
