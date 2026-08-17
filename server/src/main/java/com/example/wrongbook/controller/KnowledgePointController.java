package com.example.wrongbook.controller;

import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.KnowledgePointRequest;
import com.example.wrongbook.service.KnowledgePointService;
import com.example.wrongbook.vo.KnowledgePointNode;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/knowledge-point")
@RequiredArgsConstructor
public class KnowledgePointController {

    private final KnowledgePointService knowledgePointService;

    @GetMapping("/tree")
    public RestResponse<List<KnowledgePointNode>> tree(@RequestParam(required = false) Long subjectId) {
        return RestResponse.ok(knowledgePointService.tree(subjectId));
    }

    @PostMapping
    @RequireRole("admin")
    public RestResponse<Long> add(@Validated @RequestBody KnowledgePointRequest request) {
        return RestResponse.ok(knowledgePointService.add(request));
    }

    @DeleteMapping("/{id}")
    @RequireRole("admin")
    public RestResponse<Void> remove(@PathVariable Long id) {
        knowledgePointService.remove(id);
        return RestResponse.ok();
    }
}
