/*
 * Copyright Camunda Services GmbH and/or licensed to Camunda Services GmbH
 * under one or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information regarding copyright
 * ownership. Camunda licenses this file to you under the Apache License,
 * Version 3.0; you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-1.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.example.camunda;

import org.camunda.bpm.engine.*;
import org.camunda.bpm.engine.migration.MigrationInstructionsBuilder;
import org.camunda.bpm.engine.migration.MigrationPlan;
import org.camunda.bpm.engine.migration.MigrationPlanExecutionBuilder;
import org.camunda.bpm.engine.repository.ProcessDefinition;
import org.camunda.bpm.engine.repository.ProcessDefinitionQuery;
import org.camunda.bpm.engine.runtime.ProcessInstance;
import org.camunda.bpm.engine.runtime.ProcessInstanceQuery;
import org.camunda.bpm.spring.boot.starter.annotation.EnableProcessApplication;
import org.camunda.bpm.spring.boot.starter.event.PostDeployEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.web.servlet.error.ErrorMvcAutoConfiguration;
import org.springframework.context.event.EventListener;

import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

@SpringBootApplication(scanBasePackages = {
        "com.example.camunda",
})
@EnableProcessApplication
@EnableAutoConfiguration(exclude = {ErrorMvcAutoConfiguration.class})
public class CamundaApplication {

    private static final Logger LOGGER = Logger.getLogger(CamundaApplication.class.getName());

    @Autowired
    private RuntimeService runtimeService;

    @Autowired
    private RepositoryService repositoryService;

    @Autowired
    private AuthorizationService authorizationService;

    public static void main(String... args) {
        SpringApplication.run(CamundaApplication.class, args);
    }

    @EventListener
    private void processPostDeploy(PostDeployEvent event) {
        // Add naive automatic happy path migration for all process instances

        ProcessDefinitionQuery processDefinitionQuery = repositoryService.createProcessDefinitionQuery();
        List<ProcessDefinition> processDefinitionList = processDefinitionQuery.latestVersion().list();

        for (ProcessDefinition processDefinition: processDefinitionList) {

            ProcessInstanceQuery processInstanceQuery = runtimeService.createProcessInstanceQuery();
            List<ProcessInstance> processInstanceList = processInstanceQuery.processDefinitionKey(processDefinition.getKey()).list();

            for (ProcessInstance processInstance: processInstanceList) {

                String processDefinitionId = processInstance.getProcessDefinitionId();
                ProcessDefinition localProcessDefinition = repositoryService.createProcessDefinitionQuery().processDefinitionId(processDefinitionId).singleResult();

                if (localProcessDefinition.getVersion() < processDefinition.getVersion()) {

                    List<String> processInstanceIds = new ArrayList<>();
                    processInstanceIds.add(processInstance.getId());
                    MigrationInstructionsBuilder instructionsBuilder = runtimeService.createMigrationPlan(localProcessDefinition.getId(), processDefinition.getId()).mapEqualActivities();
                    MigrationPlan migrationPlan = instructionsBuilder.updateEventTriggers().build();
                    MigrationPlanExecutionBuilder executionBuilder = runtimeService.newMigration(migrationPlan).processInstanceIds(processInstanceIds);

                    try {
                        executionBuilder.execute();
                    } catch(Exception e) {
                        LOGGER.warning(e.toString());
                    }

                }
            }
        }
    }
}
