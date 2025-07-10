using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;
using System.IO;
using System;

public class Task1B : MonoBehaviour
{
    // Text
    [SerializeField] private TextMeshProUGUI step_counter;
    [SerializeField] private TextMeshProUGUI light_label;
    [SerializeField] private TextMeshProUGUI medium_label;
    [SerializeField] private TextMeshProUGUI hard_label;

    // Managers
    [SerializeField] private UDP_Listener udp_listener;
    [SerializeField] private TaskManager taskManager;
    [SerializeField] private GameObject taskParent;

    // Cubes
    [SerializeField] private GameObject cubeLight;
    [SerializeField] private GameObject cubeMedium;
    [SerializeField] private GameObject cubeHard;
    [SerializeField] private GameObject hardX;
    [SerializeField] private GameObject mediumX;
    [SerializeField] private GameObject lightX;

    // Selectors
    [SerializeField] private GameObject selector;

    // Materials
    [SerializeField] private Material greenMat;
    [SerializeField] private Material yellowMat;
    [SerializeField] private Material redMat;

    // Colours
    private Color white;
    private Color red;
    private Color yellow;
    private Color green;

    // Loop variables
    private int steps = 0;
    private bool awaitingInput = false;
    private bool taskFinished = false;
    private int target = 0;

    // Selector original position
    private Vector3 selectorOriginalPosition;

    // Data logging
    private int correct_answers = 0;
    private int total_answers = 0;
    private float[] time_to_target = new float[10]; // time in s in format 0.00

    private List<char> target_by_step = new List<char>();
    private List<char> answer_by_step = new List<char>();

    private List<char> all_targets = new List<char>(); // to store each target in an array
    private List<int[]> all_presures = new List<int[]>(); // store full pressure array

    private float timeStart = 0f;

    // Pressure-related
    public int th_light = 5;
    public int th_medium = 33;
    public int th_hard = 66;
    private float time_level = 2f; // seconds to count a level as an answer

    private float pressureHoldStartTime = 0f;
    private string currentPressureLevel = "";
    private bool pressureLevelDetected = false;
    private string user_answer = "";

    private void Start()
    {
        // Initialize colors from labels
        red = hard_label.color;
        yellow = medium_label.color;
        green = light_label.color;
        white = Color.white;

        // Set all labels to white
        hard_label.color = white;
        medium_label.color = white;
        light_label.color = white;

        // Hide Xs
        hardX.SetActive(false);
        mediumX.SetActive(false);
        lightX.SetActive(false);

        // Hide cubes
        cubeLight.SetActive(false);
        cubeMedium.SetActive(false);
        cubeHard.SetActive(false);

        // Save selector original position
        selectorOriginalPosition = selector.transform.localPosition;
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
        while (steps < 10) // Fixed number of steps
        {
            target = UnityEngine.Random.Range(1, 4); // 1 = light, 2 = medium, 3 = hard

            // Reset selector
            selector.transform.localPosition = selectorOriginalPosition;

            // Set up target visuals
            switch (target)
            {
                case 1:
                    light_label.color = green;
                    cubeLight.SetActive(true);
                    lightX.SetActive(true);
                    break;
                case 2:
                    medium_label.color = yellow;
                    cubeMedium.SetActive(true);
                    mediumX.SetActive(true);
                    break;
                case 3:
                    hard_label.color = red;
                    cubeHard.SetActive(true);
                    hardX.SetActive(true);
                    break;
            }

            step_counter.text = $"{steps + 1} / 10";

            awaitingInput = true;
            pressureHoldStartTime = 0f;
            currentPressureLevel = "";
            pressureLevelDetected = false;
            user_answer = "";

            // time to target starts counting now
            timeStart = Time.time;

            // Wait until user holds a valid pressure level for required seconds
            yield return new WaitUntil(() => pressureLevelDetected || taskFinished);

            // time to target stops counting now
            time_to_target[steps] = Time.time - timeStart;

            // Save target in this step
            target_by_step.Add(TargetToChar(target));

            // Save answer in this step
            answer_by_step.Add(user_answer.Length > 0 ? user_answer[0] : '-');

            if (taskFinished) yield break;

            awaitingInput = false;

            int selectedIndex = CharToTarget(user_answer);
            if (selectedIndex == target)
                correct_answers++;

            total_answers++;
            steps++;

            // Reset visuals
            light_label.color = white;
            medium_label.color = white;
            hard_label.color = white;

            cubeLight.SetActive(false);
            cubeMedium.SetActive(false);
            cubeHard.SetActive(false);

            lightX.SetActive(false);
            mediumX.SetActive(false);
            hardX.SetActive(false);

            yield return new WaitForSeconds(1.5f);
        }

        FinishTask();
    }

    private void HandleClassInput(UDP_Listener.UdpData data)
    {
        if (!awaitingInput) return;

        int[] pressure = data.Pressure;
        if (pressure == null || pressure.Length < 3) return;

        int maxPressure = Mathf.Max(pressure[0], pressure[1], pressure[2]);

        // Save data
        all_presures.Add((int[])pressure.Clone()); // Save all 3 channels
        all_targets.Add(TargetToChar(target));

        // Update selector position
        float normalizedPressure = maxPressure / 100f;
        selector.transform.localPosition = new Vector3(
            selectorOriginalPosition.x,
            Mathf.Lerp(selectorOriginalPosition.y, 1.13f, normalizedPressure),
            selectorOriginalPosition.z
        );

        Debug.Log(normalizedPressure + ", " + Mathf.Lerp(selectorOriginalPosition.y, 1.13f, normalizedPressure) + ", " + selectorOriginalPosition.y);


        // Determine pressure level
        string newLevel = "";
        if (maxPressure >= th_light && maxPressure < th_medium)
            newLevel = "l";
        else if (maxPressure >= th_medium && maxPressure < th_hard)
            newLevel = "m";
        else if (maxPressure >= th_hard)
            newLevel = "h";

        if (newLevel == "")
        {
            pressureHoldStartTime = 0f;
            currentPressureLevel = "";
            return;
        }

        if (newLevel != currentPressureLevel)
        {
            currentPressureLevel = newLevel;
            pressureHoldStartTime = Time.time;
        }
        else
        {
            if (Time.time - pressureHoldStartTime >= time_level)
            {
                pressureLevelDetected = true;
                user_answer = newLevel;
            }
        }
    }

    private int CharToTarget(string input)
    {
        switch (input.ToLower())
        {
            case "l": return 1;
            case "m": return 2;
            case "h": return 3;
            default: return -1;
        }
    }

    private char TargetToChar(int index)
    {
        switch (index)
        {
            case 1: return 'l';
            case 2: return 'm';
            case 3: return 'h';
            default: return '-';
        }
    }

    public void FinishTask()
    {
        taskFinished = true;
        Debug.Log($"Finished Task: Correct Answers = {correct_answers}, Total Answers = {total_answers}");

        string timestamp = DateTime.Now.ToString("dd_HH_mm");
        string fileName = $"task1B_{timestamp}.csv";
        string path = @"C:\Quick_Disk\tonge_project\tongue_XR\Data_Logging\" + fileName;

        using (StreamWriter writer = new StreamWriter(path))
        {
            // Header
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

                string stepTarget = i < target_by_step.Count ? target_by_step[i].ToString() : "-";
                string stepInput = i < answer_by_step.Count ? answer_by_step[i].ToString() : "-";
                string time = i < time_to_target.Length ? time_to_target[i].ToString("F2", System.Globalization.CultureInfo.InvariantCulture) : "-";
                string allTarget = i < all_targets.Count ? all_targets[i].ToString() : "-";

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

            Debug.Log("CSV created");
        }

        udp_listener.OnDataReceived -= HandleClassInput;
        taskManager.IntermediatePanel();
        taskParent.SetActive(false);
        this.gameObject.SetActive(false);
    }
}
