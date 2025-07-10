using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;

public class Task1C : MonoBehaviour
{
    // Text
    [SerializeField] private TextMeshProUGUI step_counter;

    // Managers
    [SerializeField] private UDP_Listener udp_listener;
    [SerializeField] private TaskManager taskManager;
    [SerializeField] private GameObject taskParent;

    // Panels
    [SerializeField] private GameObject panels; // 9 children ordered hard-left → light-right

    // Selectors
    [SerializeField] private GameObject selectorLeft;
    [SerializeField] private GameObject selectorFront;
    [SerializeField] private GameObject selectorRight;
    private Vector3[] selectorOriginalPositions = new Vector3[3]; // [0]=left, [1]=front, [2]=right

    // Task logic
    private int steps = 0;
    private bool awaitingInput = false;
    private bool taskFinished = false;
    private int targetLevel = 0;  // 1=light, 2=medium, 3=hard
    private int targetSide = 0;   // 0=left, 1=front, 2=right

    // Data logging
    private int correct_answers = 0;
    private int total_answers = 0;
    private float[] time_to_target = new float[10];

    private List<string> target_by_step = new List<string>(); // e.g. "h-left"
    private List<string> answer_by_step = new List<string>(); // same format
    private List<string> all_targets = new List<string>();    // same format
    private List<int[]> all_presures = new List<int[]>();

    private float timeStart = 0f;

    // Pressure detection
    public int th_light = 5;
    public int th_medium = 33;
    public int th_hard = 66;
    private float time_level = 2f;

    private float pressureHoldStartTime = 0f;
    private string currentPressureLevel = "";
    private string currentSide = "";
    private bool pressureLevelDetected = false;
    private string user_answer = "";

    private void Start()
    {
        // Store selector initial positions
        selectorOriginalPositions[0] = selectorLeft.transform.localPosition;
        selectorOriginalPositions[1] = selectorFront.transform.localPosition;
        selectorOriginalPositions[2] = selectorRight.transform.localPosition;

        // Deactivate panel highlights
        for (int i = 0; i < panels.transform.childCount; i++)
        {
            panels.transform.GetChild(i).gameObject.SetActive(false);
        }
    }

    public void Hide() => taskParent.SetActive(false);
    public void Show() => taskParent.SetActive(true);

    public void StartTask()
    {
        steps = 0;
        correct_answers = 0;
        total_answers = 0;
        taskFinished = false;
        pressureLevelDetected = false;
        user_answer = "";

        udp_listener.OnDataReceived += HandleClassInput;
        StartCoroutine(SelectionLoop());
    }

    private IEnumerator SelectionLoop()
    {
        while (steps < 10)
        {
            // Random target selection
            targetLevel = UnityEngine.Random.Range(1, 4); // 1=light, 2=medium, 3=hard
            targetSide = UnityEngine.Random.Range(1, 4);  // 1=left, 2=front, 3=right

            // Activate correct panel
            int panelIndex = (targetLevel - 1) * 3 + targetSide-1;
            GameObject targetPanel = panels.transform.GetChild(panelIndex).gameObject;
            targetPanel.SetActive(true);

            // Step counter
            step_counter.text = $"{steps + 1} / 10";

            // Reset input
            awaitingInput = true;
            pressureHoldStartTime = 0f;
            currentPressureLevel = "";
            pressureLevelDetected = false;
            user_answer = "";

            timeStart = Time.time;

            // Wait until valid pressure held
            yield return new WaitUntil(() => pressureLevelDetected || taskFinished);

            time_to_target[steps] = Time.time - timeStart;

            // Reset the selectors' positions
            selectorLeft.transform.localPosition = selectorOriginalPositions[0];
            selectorFront.transform.localPosition = selectorOriginalPositions[1];
            selectorRight.transform.localPosition = selectorOriginalPositions[2];

            // Store results
            string targetStr = PressureLevelToChar(targetLevel) + "-" + SideIndexToName(targetSide);
            target_by_step.Add(targetStr);
            answer_by_step.Add(user_answer != "" ? user_answer : "-");

            if (taskFinished) yield break;

            if (user_answer == targetStr)
                correct_answers++;

            total_answers++;
            steps++;

            // Reset panels
            targetPanel.SetActive(false);
            yield return new WaitForSeconds(1.5f);
        }

        FinishTask();
    }

    private void HandleClassInput(UDP_Listener.UdpData data)
    {
        if (!awaitingInput) return;
        int[] pressure = data.Pressure;
        if (pressure == null || pressure.Length < 3) return;

        all_presures.Add((int[])pressure.Clone());

        int maxIndex = GetMaxIndex(pressure);
        int maxPressure = pressure[maxIndex];

        // Move corresponding selector, only the selector with the highest pressur
        float normalized = maxPressure / 100f;
        GameObject sel = GetSelectorBySide(maxIndex+1);
        Vector3 original = selectorOriginalPositions[maxIndex];
        sel.transform.localPosition = new Vector3(
            original.x,
            Mathf.Lerp(original.y, 1.38f, normalized),
            original.z
        );

        string levelStr = "";
        if (maxPressure >= th_light && maxPressure < th_medium) 
            levelStr = "l";
        else if (maxPressure >= th_medium && maxPressure < th_hard) 
            levelStr = "m";
        else if (maxPressure >= th_hard) 
            levelStr = "h";

        string sideStr = SideIndexToName(maxIndex+1);

        if (string.IsNullOrEmpty(levelStr))
        {
            pressureHoldStartTime = 0f;
            currentPressureLevel = "";
            currentSide = "";
            return;
        }

        if (levelStr != currentPressureLevel || sideStr != currentSide)
        {
            currentPressureLevel = levelStr;
            currentSide = sideStr;
            pressureHoldStartTime = Time.time;
        }
        else
        {
            if (Time.time - pressureHoldStartTime >= time_level)
            {
                pressureLevelDetected = true;
                user_answer = levelStr + "-" + sideStr;
            }
        }

        all_targets.Add(PressureLevelToChar(targetLevel) + "-" + SideIndexToName(targetSide));
    }

    private GameObject GetSelectorBySide(int index)
    {
        switch (index)
        {
            case 1: return selectorLeft;
            case 2: return selectorFront;
            case 3: return selectorRight;
            default: return null;
        }
    }

    private int GetMaxIndex(int[] arr)
    {
        int max = arr[0], index = 0;
        for (int i = 1; i < arr.Length; i++)
        {
            if (arr[i] > max)
            {
                max = arr[i];
                index = i;
            }
        }
        return index;
    }

    private string SideIndexToName(int index)
    {
        return index switch
        {
            1 => "left",
            2 => "front",
            3 => "right",
            _ => "unknown",
        };
    }

    private char PressureLevelToChar(int level)
    {
        return level switch
        {
            1 => 'l',
            2 => 'm',
            3 => 'h',
            _ => '-',
        };
    }

    public void FinishTask()
    {
        taskFinished = true;
        Debug.Log($"Finished Task: Correct Answers = {correct_answers}, Total Answers = {total_answers}");

        string timestamp = DateTime.Now.ToString("dd_HH_mm");
        string fileName = $"task1C_{timestamp}.csv";
        string path = @"C:\Quick_Disk\tonge_project\tongue_XR\Data_Logging\" + fileName;

        using (StreamWriter writer = new StreamWriter(path))
        {
            writer.WriteLine("CorrectAnswers;TotalAnswers;TargetByStep;AnswerByStep;TimeToTarget;AllTargets;PressureLeft;PressureFront;PressureRight");

            int maxRows = Mathf.Max(
                1,
                target_by_step.Count,
                answer_by_step.Count,
                time_to_target.Length,
                all_targets.Count,
                all_presures.Count
            );

            for (int i = 0; i < maxRows; i++)
            {
                string correctAns = i == 0 ? correct_answers.ToString() : "-";
                string totalAns = i == 0 ? total_answers.ToString() : "-";
                string stepTarget = i < target_by_step.Count ? target_by_step[i] : "-";
                string stepInput = i < answer_by_step.Count ? answer_by_step[i] : "-";
                string time = i < time_to_target.Length ? time_to_target[i].ToString("F2", System.Globalization.CultureInfo.InvariantCulture) : "-";
                string allTarget = i < all_targets.Count ? all_targets[i] : "-";

                string p1 = "-", p2 = "-", p3 = "-";
                if (i < all_presures.Count)
                {
                    int[] p = all_presures[i];
                    if (p.Length >= 3)
                    {
                        p1 = p[0].ToString();
                        p2 = p[1].ToString();
                        p3 = p[2].ToString();
                    }
                }

                writer.WriteLine($"{correctAns};{totalAns};{stepTarget};{stepInput};{time};{allTarget};{p1};{p2};{p3}");
            }
        }

        udp_listener.OnDataReceived -= HandleClassInput;
        taskManager.IntermediatePanel();
        taskParent.SetActive(false);
        this.gameObject.SetActive(false);
    }
}
