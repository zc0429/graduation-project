package com.example.wrongbook.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.entity.Message;

/**
 * 消息通知服务（论文 5.3 类设计 (10)）：复习提醒、报告生成等系统消息的
 * 生成、分页查询与已读状态维护
 */
public interface MessageService {

    /** 发送系统消息（供各业务模块调用） */
    void send(Long userId, String type, String title, String content);

    /** 消息分页（本人，可按已读状态筛选） */
    Page<Message> page(Integer pageNum, Integer pageSize, Integer isRead);

    /** 标记已读（本人） */
    void markRead(Long id);

    /** 未读数量（本人，用于消息角标） */
    Long unreadCount();
}
