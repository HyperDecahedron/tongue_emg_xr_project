using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;
using System.IO;
using System;

public class Task1A : MonoBehaviour
{
    // Text
    [SerializeField] private TextMeshProUGUI step_counter;
    [SerializeField] private TextMeshProUGUI left_label;
    [SerializeField] private TextMeshProUGUI front_label;
    [SerializeField] private TextMeshProUGUI right_label;

    // Managers
    [SerializeField] private UDP_Listener udp_listener;
    [SerializeField] private TaskManager taskManager;
    [SerializeField] private GameObject taskParent;

    // Cubes
    [SerializeField] private GameObject cubeLeft;
    [SerializeField] private GameObject cubeFront;
    [SerializeField] private GameObject cubeRight;

    // Selectors
    [SerializeField] private GameObject selectorLeft;
    [SerializeField] private GameObject selectorFront;
    [SerializeField] private GameObject selectorRight;

    // Materials
    [SerializeField] private Material greenMat;
    [SerializeField] private Material yellowMat;
    [SerializeField] private Material redMat;
    [SerializeField] private Material blueMat;

    // Colours
    private Color white;
    private Color red;
    private Color yellow;
    private Color green;

    private int steps = 0;
    private bool awaitingInput = false;

    private string lastInput = "";
    private int consecutiveCount = 0;
    private int classes_in_a_row = 3;
    private bool taskFinished = false;

    private int target = 0;

    // Data logging
    private int correct_answers = 0;
    private int total_answers = 0;
    private float[] time_to_target = new float[10]; // time in s in format 0.00, each is the time to reach each target in every step

    private List<char> targets = new List<char>();
    private List<char> inputs = new List<char>();

    private List<char> all_targets = new List<char>(); // to store each target in an array
    private List<char> all_inputs = new List<char>(); // same but to store the inputs. at the end, both should have the same size

    private float timeStart = 0f;

    private void Start()
    {
        // Initialize colors from labels
        red = right_label.color;
        yellow = front_label.color;
        green = left_label.color;
        white = Color.white;

        // Set all labels to white
        right_label.color = white;
        front_label.color = white;
        left_label.color = white;

        // Hide selectors except left
        selectorLeft.SetActive(false);
        selectorFront.SetActive(false);
        selectorRight.SetActive(false);

        left_label.color = white;
        front_label.color = white;
        right_label.color = white;

        cubeLeft.GetComponent<Renderer>().material = blueMat;
        cubeFront.GetComponent<Renderer>().material = blueMat;
        cubeRight.GetComponent<Renderer>().material = blueMat;

        cubeLeft.GetComponent<RotateCube>().enabled = false;
        cubeFront.GetComponent<RotateCube>().enabled = false;
        cubeRight.GetComponent<RotateCube>().enabled = false;
    }

    public void Hide() => taskParent.SetActive(false);
    public void Show() => taskParent.SetActive(true);

    public void StartTask()
    {
        steps = 0;
        correct_answers = 0;
        total_answers = 0;
        taskFinished = false;

        udp_listener.OnClassReceived += HandleClassInput;
        StartCoroutine(SelectionLoop());
    }

    private IEnumerator SelectionLoop()
    {
        while (steps < 10) // Fixed number of steps
        {
            target = UnityEngine.Random.Range(1, 4); // 1, 2, or 3

            // Reset label colors and cube materials
            selectorLeft.SetActive(false);
            selectorFront.SetActive(false);
            selectorRight.SetActive(false);

            // Set up target visuals
            switch (target)
            {
                case 1: // Left
                    left_label.color = green;
                    cubeLeft.GetComponent<RotateCube>().enabled = true;
                    cubeLeft.GetComponent<Renderer>().material = greenMat;
                    break;
                case 2: // Front
                    front_label.color = yellow;
                    cubeFront.GetComponent<RotateCube>().enabled = true;
                    cubeFront.GetComponent<Renderer>().material = yellowMat;
                    break;
                case 3: // Right
                    right_label.color = red;
                    cubeRight.GetComponent<RotateCube>().enabled = true;
                    cubeRight.GetComponent<Renderer>().material = redMat;
                    break;
            }

            step_counter.text = $"{steps + 1} / 10";

            awaitingInput = true;
            lastInput = "";
            consecutiveCount = 0;

            // time to target starts counting now
            timeStart = Time.time;

            // Wait until user gives the correct input `classes_in_a_row` times
            yield return new WaitUntil(() => consecutiveCount >= classes_in_a_row || taskFinished);

            // time to target stops counting now
            time_to_target[steps] = Time.time - timeStart;

            // add current target and lastInput to targets and selections
            switch (target)
            {
                case 1: targets.Add('l'); break;
                case 2: targets.Add('f'); break;
                case 3: targets.Add('r'); break;
            }
            inputs.Add(lastInput[0]);

            if (taskFinished) yield break;

            awaitingInput = false;
            int selectedIndex = GetTargetIndexFromInput(lastInput); // 1, 2, or 3

            // Make pyramidal selector appear as a visual feedback of the selected cube.
            switch (selectedIndex)
            {
                case 1: selectorLeft.SetActive(true); break;
                case 2: selectorFront.SetActive(true); break;
                case 3: selectorRight.SetActive(true); break;
            }

            if (selectedIndex == target)
                correct_answers++;

            total_answers++;
            steps++;

            // Reset things
            left_label.color = white;
            front_label.color = white;
            right_label.color = white;

            cubeLeft.GetComponent<Renderer>().material = blueMat;
            cubeFront.GetComponent<Renderer>().material = blueMat;
            cubeRight.GetComponent<Renderer>().material = blueMat;

            cubeLeft.GetComponent<RotateCube>().enabled = false;
            cubeFront.GetComponent<RotateCube>().enabled = false;
            cubeRight.GetComponent<RotateCube>().enabled = false;

            yield return new WaitForSeconds(2f);
        }

        FinishTask();
    }

    private void HandleClassInput(string input)
    {
        if (!awaitingInput) return;

        if (input == lastInput)
        {
            consecutiveCount++;
        }
        else
        {
            lastInput = input;
            consecutiveCount = 1;
        }

        // save one instance of current target in targets and add the current input to inputs
        switch (target)
        {
            case 1: all_targets.Add('l'); break;
            case 2: all_targets.Add('f'); break;
            case 3: all_targets.Add('r'); break;
        }

        if (input.Length > 0)
            all_inputs.Add(input[0]);

        // update selector position
        selectorLeft.SetActive(false);
        selectorFront.SetActive(false);
        selectorRight.SetActive(false);

        switch (input)
        {
            case "l":
                selectorLeft.SetActive(true);
                break;
            case "f":
                selectorFront.SetActive(true);
                break;
            case "r":
                selectorRight.SetActive(true);
                break;
        }
    }

    private int GetTargetIndexFromInput(string input)
    {
        switch (input.ToLower())
        {
            case "l": return 1;
            case "f": return 2;
            case "r": return 3;
            default: return -1;
        }
    }

    public void FinishTask()
    {
        taskFinished = true;
        Debug.Log($"Finished Task: Correct Answers = {correct_answers}, Total Answers = {total_answers}");

        string timestamp = DateTime.Now.ToString("dd_HH_mm");
        string fileName = $"task1A_{timestamp}.csv";
        string path = @"C:\Quick_Disk\tonge_project\tongue_XR\Data_Logging\" + fileName;

        using (StreamWriter writer = new StreamWriter(path))
        {
            // Header
            writer.WriteLine("CorrectAnswers;TotalAnswers;StepTargets;StepInputs;TimeToTarget;AllTargets;AllInputs");

            int maxRows = Mathf.Max(
                1, // At least one row for correct/total answers
                targets.Count,
                inputs.Count,
                time_to_target.Length,
                all_targets.Count,
                all_inputs.Count
            );

            for (int i = 0; i < maxRows; i++)
            {
                string correctAns = i == 0 ? correct_answers.ToString() : "-";
                string totalAns = i == 0 ? total_answers.ToString() : "-";

                string stepTarget = i < targets.Count ? targets[i].ToString() : "-";
                string stepInput = i < inputs.Count ? inputs[i].ToString() : "-";

                //Force decimal separator to be a period (.)
                string time = i < time_to_target.Length ? time_to_target[i].ToString("F2", System.Globalization.CultureInfo.InvariantCulture) : "-";

                string allTarget = i < all_targets.Count ? all_targets[i].ToString() : "-";
                string allInput = i < all_inputs.Count ? all_inputs[i].ToString() : "-";

                writer.WriteLine($"{correctAns};{totalAns};{stepTarget};{stepInput};{time};{allTarget};{allInput}");
            }
            Debug.Log("CSV created");
        }

        udp_listener.OnClassReceived -= HandleClassInput;
        taskManager.IntermediatePanel();
        taskParent.SetActive(false);
        this.gameObject.SetActive(false);
    }

}
