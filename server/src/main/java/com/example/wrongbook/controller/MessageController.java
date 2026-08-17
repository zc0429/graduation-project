package com.example.wrongbook.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.entity.Message;
import com.example.wrongbook.service.MessageService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/message")
@RequiredArgsConstructor
public class MessageController {

    private final MessageService messageService;

    @GetMapping("/page")
    public RestResponse<Page<Message>> page(@RequestParam(defaultValue = "1") Integer pageNum,
                                            @RequestParam(defaultValue = "10") Integer pageSize,
                                            @RequestParam(required = false) Integer isRead) {
        return RestResponse.ok(messageService.page(pageNum, pageSize, isRead));
    }

    @PutMapping("/{id}/read")
    public RestResponse<Void> markRead(@PathVariable Long id) {
        messageService.markRead(id);
        return RestResponse.ok();
    }

    @GetMapping("/unread-count")
    public RestResponse<Long> unreadCount() {
        return RestResponse.ok(messageService.unreadCount());
    }
}
