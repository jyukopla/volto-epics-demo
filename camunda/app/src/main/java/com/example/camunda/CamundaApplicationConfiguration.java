package com.example.camunda;

import org.camunda.bpm.engine.ProcessEngineConfiguration;
import org.camunda.bpm.engine.impl.incident.IncidentHandler;
import org.camunda.bpm.engine.runtime.Incident;
import org.camunda.bpm.engine.spring.SpringProcessEngineConfiguration;
import org.camunda.bpm.spring.boot.starter.configuration.Ordering;
import org.camunda.bpm.spring.boot.starter.configuration.impl.AbstractCamundaConfiguration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
@Order(Ordering.DEFAULT_ORDER + 1)
public class CamundaApplicationConfiguration extends AbstractCamundaConfiguration {

    @Override
    public void preInit(SpringProcessEngineConfiguration springProcessEngineConfiguration) {
        // Raise incidents on unhandled BPMN errors instead of stopping processes
        springProcessEngineConfiguration.setEnableExceptionsAfterUnhandledBpmnError(true);

        // Set default serialization format to application/json for easier variable API
        springProcessEngineConfiguration.setDefaultSerializationFormat("application/json");

        // Save full history
        springProcessEngineConfiguration.setHistory(ProcessEngineConfiguration.HISTORY_FULL);

        // Configure history cleanup
        springProcessEngineConfiguration.setHistoryRemovalTimeStrategy("end");
        springProcessEngineConfiguration.setHistoryTimeToLive("P7D");
        springProcessEngineConfiguration.setHistoryCleanupBatchSize(100);
        springProcessEngineConfiguration.setHistoryCleanupBatchWindowEndTime("06:00");
        springProcessEngineConfiguration.setHistoryCleanupBatchWindowStartTime("22:00");
        springProcessEngineConfiguration.setHistoryCleanupDegreeOfParallelism(1);
        springProcessEngineConfiguration.setHistoryCleanupEnabled(true);
        springProcessEngineConfiguration.setHistoryCleanupStrategy("removalTimeBased");
    }
}
