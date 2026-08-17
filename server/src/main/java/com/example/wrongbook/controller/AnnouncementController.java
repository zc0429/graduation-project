package com.example.wrongbook.controller;

import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.AnnouncementRequest;
import com.example.wrongbook.entity.Announcement;
import com.example.wrongbook.service.AnnouncementService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/announcement")
@RequiredArgsConstructor
public class AnnouncementController {

    private final AnnouncementService announcementService;

    @GetMapping("/list")
    public RestResponse<List<Announcement>> list() {
        return RestResponse.ok(announcementService.list());
    }

    @PostMapping
    @RequireRole("admin")
    public RestResponse<Long> publish(@Validated @RequestBody AnnouncementRequest request) {
        return RestResponse.ok(announcementService.publish(request));
    }
}
