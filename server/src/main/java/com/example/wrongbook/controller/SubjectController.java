package com.example.wrongbook.controller;

import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.SubjectRequest;
import com.example.wrongbook.entity.Subject;
import com.example.wrongbook.service.SubjectService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/subject")
@RequiredArgsConstructor
public class SubjectController {

    private final SubjectService subjectService;

    @GetMapping("/list")
    public RestResponse<List<Subject>> list() {
        return RestResponse.ok(subjectService.list());
    }

    @PostMapping
    @RequireRole("admin")
    public RestResponse<Long> add(@Validated @RequestBody SubjectRequest request) {
        return RestResponse.ok(subjectService.add(request));
    }

    @PutMapping("/{id}")
    @RequireRole("admin")
    public RestResponse<Void> update(@PathVariable Long id, @Validated @RequestBody SubjectRequest request) {
        subjectService.update(id, request);
        return RestResponse.ok();
    }
}
